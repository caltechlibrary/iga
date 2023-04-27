# Record metadata

A record in [InvenioRDM](https://inveniosoftware.org/products/rdm/) is serialized to/from [JSON](https://en.wikipedia.org/wiki/JSON) format. A complete record has the following top-level fields, but to create a new record, a client only needs to provide the data for the `metadata` field – the others are added by the InvenioRDM server.
```{code-block} javascript
{
   "access" : { ... },
   "created": "...",
   "files" : { ... },
   "id": "...",
   "links" : { ... },
   "metadata" : { ... },
   "parent": { ... },
   "pids" : { ... },
   "revision_id": N,
   "status": "...",
   "updated": "...",
}
```

The purpose of IGA is to construct the `metadata` field according to the [InvenioRDM metadata definition](https://inveniordm.docs.cern.ch/reference/metadata). The subfields inside `metadata` are described below.


## Subfields of `metadata`

 The following are the possible subfields inside the `metadata` field and their meanings, as well as some information about how IGA treats them.
```{code-block} javascript
"metadata": {
    "additional_descriptions": [ ... ],
    "additional_titles": [ ... ],
    "contributors": [ ... ],
    "creators": [ ... ],
    "dates": [ ... ],
    "description": "...",
    "formats": [],
    "funding": [ ... ],
    "identifiers": [ ... ],
    "languages": [ ... ],
    "locations": {},
    "publication_date": "...",
    "publisher": "...",
    "references": [ ... ],
    "related_identifiers": [ ... ],
    "resource_type": { ... },
    "rights": [ ... ],
    "sizes": [],
    "subjects": [ ... ],
    "title": "...",
    "version": "...",
}
```

* `additional_descriptions`: a record for a software release has a primary `description` field (see below) that IGA obtains from the description of the software release in GitHub. The "additional" descriptions are other descriptions (e.g., release notes) meant to supplement the primary description.
* `additional_titles`: a record for a software release has a primary `title` field (see below) that IGA creates using a combination of the software name and the version. The "additional" titles are other descriptions that IGA finds in the `codemeta.json` and/or `CITATION.cff` files.
* `contributors`: persons or organizations who contributed somehow to the development or maintenance of the software. IGA draws on `codemeta.json`, `CITATION.cff`, and optionally, the GitHub repository's list of contributors.
* `creators`: the persons and/or organizations credited for creating the software. IGA draws on the `codemeta.json` and `CITATION.cff` files to determine this; if the files are not available or don't contain the necessary fields, IGA falls back to using the author of the GitHub release or the repository owner (in that order).
* `dates`: various dates relevant to the software (apart from the publication date in the InvenioRDM server, which is stored separately). IGA looks in the `codemeta.json` and `CITATION.cff` files for these dates.
* `description`: the description given to the software release in GitHub. If none is provided, IGA looks into the `codemeta.json` or `CITATION.cff` files.
* `formats`: currently left unfilled by IGA as it does not appear to be of any use to InvenioRDM.
* `funding`: information about financial support (funding) for the software. The `codemeta.json` file is the only source for this information that IGA can use for this; neither `CITATION.cff` nor GitHub provide explicit fields for funding information.
* `identifiers`: this field is confusingly named in InvenioRDM – a better name would have been `additional_identifiers`, because InvenioRDM assigns a primary identifier automatically in a separate field. In any case, the `identifiers` field is used to store additional persistent identifiers such as arXiv identifiers for publications.
* `languages`: the language(s) used in the software resource. Currently, this is hardwired by IGA to English.
* `locations`: InvenioRDM defines this field as "spatial region or named place where the data was gathered or about which the data is focused". Unfortunately, there are no relevant data fields in `codemeta.json`, `CITATION.cff`, or the GitHub release and repository from where location information can be extracted, so IGA has to leave this field blank.
* `publication_date`: this is defined as the date "when the resource was made available", which is not necessarily the date when it was submitted to InvenioRDM. IGA looks for the publicateion date in the `codemeta.json` or `CITATION.cff` file, if given; otherwise, it uses the date of the release in GitHub.
* `publisher`: this is defined as "the name of the entity that holds, archives, publishes, prints, distributes, releases, issues, or produces the resource." IGA sets this to the name of the InvenioRDM server.
* `references`: this field holds a list of formatted references to publications about the software or data resource. Both `codemeta.json` and `CITATION.cff` provide fields for storing reference information; IGA looks there and constructs text strings containing references formatted according to [APA 7](https://apastyle.apa.org/style-grammar-guidelines/references) guidelines.
* `related_identifiers`: this is a list of identifiers to resources related (somehow) to the software or data release. IGA takes this broadly and uses a large number of fields in `codemeta.json` and `CITATION.cff` files to generate the value of this field in the InvenioRDM record. This includes a home page URL for the software or data, issue trackers, and more.
* `resource_type`: this is assigned the value `dataset` if and only if the `CITATION.cff` file exists in the repository and has a value of `dataset` in the `type` field. Otherwise, IGA sets this InvenioRDM metadata field to `software`. There is no other way for IGA to assess the true contents of a repository, and as most GitHub repositories are for software projects, this is deemed a reasonable default.
* `rights`: this refers to the license under which the software or data is made available. Both `codemeta.json` and `CITATION.cff` have fields to express this information; if neither file is available or the relevant field is not set in the files, IGA checks the GitHub repository metadata for the license inferred by GitHub; and if that fails, IGA tries to look in the repository for a file named according to common conventions, like `LICENSE`.
* `sizes`: currently left unfilled by IGA as it does not appear to be of any use to InvenioRDM.
* `subjects`: a list of subject keywords. IGA looks in the `keywords` field offered by both `codemeta.json` and `CITATION.cff`; it also uses the `programmingLanguages` field of `codemeta.json`, and optionally, the subject keywords provided in the GitHub repository metadata.
* `title`: IGA constructs the title from two parts. For the first part, it looks to the `codemeta.json` and `CITATION.cff` files for the fields `name` and `title`, respectively; if neither are available, it uses the GitHub repository name. For the second part, IGA uses the name of the GitHub release, or if that is missing, it uses the git tag name of the GitHub release.
* `version`: for this, IGA uses the git tag of the GitHub release. If the tag is of the form "_vX.Y.Z_" or "_version X.Y.Z_" or similar, IGA strips off the leading `v` or `version`.


## Detailed field mappings

The algorithms implemented in IGA are designed to try very hard to extract automatically as much metadata as possible. Because there are four possible sources of metadata (`codemeta.json`, `CITATION.cff`, the GitHub release, and the GitHub repository), and some of them overlap in what they store, it leads to a complex set of possibilities. The table below attempts to summarize how IGA goes about filling each field. Note that some fields contain a single value, while others contain a list of multiple values.

<div id="metadata-table">

| Metadata                  | Method |
|---------------------------|--------|
| `additional_descriptions` | Add separate items as follows: <br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `releaseNotes` is set and it’s not a URL and we didn’t use it as the value of the main `description`, add it with the InvenioRDM CV value `"other"`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `description` is set and we didn’t use it as the value of the main `description`, add it with the InvenioRDM CV value `"other"`. <br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CFF `abstract` is set and we didn’t use it as the value of the main `description`, add it with the InvenioRDM CV value `"other"`. <br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the GitHub repo `description` is set and we didn’t use it as the value of the main `description`, add it with the InvenioRDM CV value `"other"`. <br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `readme` is set and it’s not a URL, add it with the InvenioRDM CV value `"technical-info"`. (If the value is a URL, create a string of the form _"Additional information is available at {URL}"_ and add that instead.)<br><br>Deduplicate the resulting list of descriptions to avoid duplicate values.|
| `additional_titles`       | Add separate items as follows:<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `name` is set, add it with InvenioRDM CV type `“alternate-title”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CFF `title` is set, add it with InvenioRDM CV type `“alternate-title”`.<br><br>Deduplicate the resulting list of descriptions to avoid duplicate values. |
| `contributors`            | Add separate items as follows:<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CFF `contact` is set, add the (single) identity with an InvenioRDM role CV value of `“contactperson”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `sponsor` is set, add each identity in the list with an InvenioRDM role CV value of `“sponsor”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `producer` is set, add each identity in the list with an InvenioRDM role CV value of `“producer”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `editor` is set, add each identity in the list with an InvenioRDM role CV value of `“editor”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `copyrightHolder` is set, add each identity in the list with an InvenioRDM role CV value of `“rightsholder”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `maintainer` is set, add each identity in the list with an InvenioRDM role CV value of `“other”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `contributor` is set, add the identities with role `“other”`; else, if CodeMeta `contributor` is not set, use the GitHub repo `contributors` field to create a list of contributors, using the GitHub API to look up people’s names, and add them with an InvenioRDM role CV value of `“other`”.<br><br>Remove identities that have a role of `“other”` and are also listed in the `creators` field. |
| `creators`                | Add separate items for each identity in the list of values from CodeMeta `author` or CFF `author` (but not both) if any are present; else, use the (single) GitHub release `author` if present; else, use the (single) GitHub repo `owner`. The method uses ORCID to look up names if only ORCID ID’s are given, as well as multiple NLP methods to split names into given/family name parts if names are given as single strings.|
| `dates`                   | Add separate items as follows:<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;An item with InvenioRDM date CV type `“created”` using the value of CodeMeta `dateCreated` (if set) or the GitHub repo `created_at`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;An item with InvenioRDM date CV type `“updated”` using the value of CodeMeta `dateModified` (if set) or the GitHub repo `updated_at`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;An item with InvenioRDM date CV type `“available”` using the value of the GitHub release `published_at`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If CodeMeta `copyrightYear` is set, an item with InvenioRDM date CV type `“copyrighted”` using the value of CodeMeta `copyrightYear`.|
| `description`             | If the GitHub release `body` is not empty, use that; else, if the CodeMeta `releaseNotes` is not empty and not a URL, use that; else, try CFF `description`, CFF `abstract`, and the GitHub repo’s `description` field, in that order.|
| `formats`                 | If the GitHub release has a value for `tarball_url`, add `“application/x-tar-gz”`. If the GitHub release has a value for `zipball_url`, add `“application/zip”`. If there are values in the GitHub release assets list, infer additional MIME types based on file extensions.|
| `funding`                 | Use CodeMeta `funding` and `funder` values, intelligently constructing InvenioRDM funding objects with names of funders (looking up ROR identifiers in ROR.org if necessary).
| `identifiers`             | For every item in CodeMeta `identifier` and CFF `identifiers`, detect recognizable identifiers of type ARXIV, DOI, GND, ISBN, ISNI, ORCID, PMCID, PMID, ROR, and SWH, and add InvenioRDM objects with scheme based on InvenioRDM identifier-types CV terms.|
| `languages`               | Hardwired to the value representing English.|
| `locations`               | Hardwired to an empty list. |
| `publication_date`        | Use CodeMeta `datePublished`, CFF `date-released`, or the GitHub release `published_at`, tried in that order.|
| `publisher`               | Use the name of the InvenioRDM server. The name is determined by downloading an existing record from the server and using the value of the `publisher` field in taht record.|
| `references`              | Look at each item in CodeMeta `referencePublication` and CFF `preferred-citation` and `references` and collect identifiers of type DOI, ARXIV, ISBN, PMCID, and PMID. Use a combination of Crossref and Python’s `isbnlib` module to get the corresponding reference metadata, then generate plain-text references in APA format, and finally add each item to the InvenioRDM references field.|
| `related_identifiers`     | Add separate items as follows:<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;The GitHub release `html_url` field value with InvenioRDM relation CV term `“isidenticalto”` and scheme `“url”`<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;The value of one of the fields CodeMeta `codeRepository`, CFF `repository-code`, or the GitHub repo `html_url` (whichever has a value first) with InvenioRDM relation CV term `“isderivedfrom”` and scheme `“url”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `issueTracker` is set, add it with the invenioRDM relation CV term `“issupplementedby”`; else if the GitHub repo `issues_url` is set, add it instead.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If the CodeMeta `releaseNotes` is a URL, add it with the invenioRDM relation CV term `“isdescribedby”`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;The value of one of the fields CodeMeta `url`, CFF `url`, or the GitHub repo `homepage` field (whichever has a value first) with InvenioRDM relation CV term `“isdescribedby”` and scheme `“url”`<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;The value of CodeMeta `sameAs` with InvenioRDM relation CV term `“isversionof”` and scheme `“url”`<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;If CodeMeta `softwareHelp` is set, or if the GitHub repo has an associated GitHub Pages URL, add one of them with InvenioRDM relation CV term `“isdocumentedby”` and scheme `“url”`<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;The value(s) of CodeMeta `relatedLink` with InvenioRDM relation CV term `“references”` and scheme `“url”`<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;For each value in the CodeMeta `referencePublication` and CFF `preferred-citation` and `references` that has not already been added as a related identifier (see above), add the identifier with InvenioRDM relation CV term `“isreferencedby”` and scheme according to the identifier type.|
| `resource_type`           | If the CFF field `type` is set to `“dataset”`, use InvenioRDM CV value `“dataset”`, otherwise in all other cases use `“software”`. |
| `rights`                  | Look for CodeMeta `license`, CFF `license`, and CFF `license-url` in that order; if none are available, look for GitHub repo `license` field value; if not set, look in the GitHub repository’s files for a file named `“LICENSE”`, `“License”`, `“COPYING”`, or similar. If the info found includes a name or a URL, match it against known SPDX licenses and use the identifier (e.g. "bsd-1-clause") as the value of the rights object's "id" field, with the title of the license as the "title" value and the URL of the license as the "link" value. If only a license file is found in the repo, create a value of the form `{"title": {"en": "License"}, "link": URL}`.|
| `sizes`                   | Not currently set, as the InvenioRDM server does not make use of it.|
| `subjects`                | Create a union of all terms found in the repo `topics` field, CodeMeta `keywords`, CFF `keywords`, CodeMeta `programmingLanguage`, and the GitHub repo `languages_url`.|
| `title`                   | Construct a string of the form _“title_part – version_part”_, using an en-dash instead of a colon to separate the parts in order to avoid accidentally introducing two colons into the string.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;For _title\_part_, use the CodeMeta `name`; if that’s not set, use the CFF `title`; and if that’s not set, use the GitHub repository `full_name`.<br>&nbsp;&nbsp;&nbsp;&bull;&nbsp;For _version\_part_, use the GitHub `release` name, or if that’s not set, the GitHub release `tag_name`.|
| `version`                 | Use the GitHub release `tag_name`, first removing any leading text of “v” or “version” if it appears as part of the tag name.|

</div>

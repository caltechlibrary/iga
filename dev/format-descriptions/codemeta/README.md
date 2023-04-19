# CodeMeta 2.0 notes

The description of the terms at <https://codemeta.github.io/terms/> does not make clear the expected hierarchical structure of a `codemeta.json` file, and neither does the crosswalk table at <https://raw.githubusercontent.com/codemeta/codemeta/master/crosswalk.csv>

Here is what we deduced as the structure. The top-level terms are drawn from:
 * `SoftwareSourceCode` from Schema.org
 * `SoftwareApplication` from Schema.org
 * `CreativeWork` from Schema.org
 * `Thing` from Schema.org
* the 10 terms introduced as additional "Codemeta terms" (bottom of <https://codemeta.github.io/terms/>)

The remaining terms in the crosswalk table and the web page of terms on the CodeMeta.github.io site are part of object structures that are used in the other terms.

This leads to the following possible top-level terms:

| Term                     | Type                      | Parent Type                 |
|--------------------------|---------------------------|-----------------------------|
| `codeRepository`         | URL                       | schema:SoftwareSourceCode   |
| `programmingLanguage`    | ComputerLanguage  or Text | schema:SoftwareSourceCode   |
| `runtimePlatform`        | Text                      | schema:SoftwareSourceCode   |
| `targetProduct`          | SoftwareApplication       | schema:SoftwareSourceCode   |
| `applicationCategory`    | Text  or URL              | schema:SoftwareApplication  |
| `applicationSubCategory` | Text  or URL              | schema:SoftwareApplication  |
| `downloadUrl`            | URL                       | schema:SoftwareApplication  |
| `fileSize`               | Text                      | schema:SoftwareApplication  |
| `installUrl`             | URL                       | schema:SoftwareApplication  |
| `memoryRequirements`     | Text  or URL              | schema:SoftwareApplication  |
| `operatingSystem`        | Text                      | schema:SoftwareApplication  |
| `permissions`            | Text                      | schema:SoftwareApplication  |
| `processorRequirements`  | Text                      | schema:SoftwareApplication  |
| `releaseNotes`           | Text  or URL              | schema:SoftwareApplication  |
| `softwareHelp`           | CreativeWork              | schema:SoftwareApplication  |
| `softwareRequirements`   | SoftwareSourceCode        | schema:SoftwareApplication  |
| `softwareVersion`        | Text                      | schema:SoftwareApplication  |
| `storageRequirements`    | Text  or URL              | schema:SoftwareApplication  |
| `supportingData`         | DataFeed                  | schema:SoftwareApplication  |
| `author`                 | Organization  or Person   | schema:CreativeWork         |
| `citation`               | CreativeWork  or URL      | schema:CreativeWork         |
| `contributor`            | Organization  or Person   | schema:CreativeWork         |
| `copyrightHolder`        | Organization  or Person   | schema:CreativeWork         |
| `copyrightYear`          | Number                    | schema:CreativeWork         |
| `dateCreated`            | Date  or DateTime         | schema:CreativeWork         |
| `dateModified`           | Date  or DateTime         | schema:CreativeWork         |
| `datePublished`          | Date                      | schema:CreativeWork         |
| `editor`                 | Person                    | schema:CreativeWork         |
| `encoding`               | MediaObject               | schema:CreativeWork         |
| `fileFormat`             | Text  or URL              | schema:CreativeWork         |
| `funder`                 | Organization or Person    | schema:CreativeWork         |
| `keywords`               | Text                      | schema:CreativeWork         |
| `license`                | CreativeWork  or URL      | schema:CreativeWork         |
| `producer`               | Organization  or Person   | schema:CreativeWork         |
| `provider`               | Organization  or Person   | schema:CreativeWork         |
| `publisher`              | Organization  or Person   | schema:CreativeWork         |
| `sponsor`                | Organization  or Person   | schema:CreativeWork         |
| `version`                | Number  or Text           | schema:CreativeWork         |
| `isAccessibleForFree`    | Boolean                   | schema:CreativeWork         |
| `isPartOf`               | CreativeWork              | schema:CreativeWork         |
| `hasPart`                | CreativeWork              | schema:CreativeWork         |
| `position`               | Integer or Text           | schema:CreativeWork         |
| `description`            | Text                      | schema:Thing                |
| `identifier`             | PropertyValue  or URL     | schema:Thing                |
| `name`                   | Text                      | schema:Thing                |
| `sameAs`                 | URL                       | schema:Thing                |
| `url`                    | URL                       | schema:Thing                |
| `relatedLink`            | URL                       | schema:Thing                |
| `softwareSuggestions`    | SoftwareSourceCode        | codemeta:SoftwareSourceCode |
| `maintainer`             | Person                    | codemeta:SoftwareSourceCode |
| `contIntegration`        | URL                       | codemeta:SoftwareSourceCode |
| `buildInstructions`      | URL                       | codemeta:SoftwareSourceCode |
| `developmentStatus`      | Text                      | codemeta:SoftwareSourceCode |
| `embargoDate`            | Date                      | codemeta:SoftwareSourceCode |
| `funding`                | Text                      | codemeta:SoftwareSourceCode |
| `issueTracker`           | URL                       | codemeta:SoftwareSourceCode |
| `referencePublication`   | ScholarlyArticle          | codemeta:SoftwareSourceCode |
| `readme`                 | URL                       | codemeta:SoftwareSourceCode |

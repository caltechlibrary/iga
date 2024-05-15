#!/usr/bin/env python3

import os.path

# Fasttext ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import fasttext

if not os.path.exists('/tmp/lid.176.bin'):
    import subprocess
    ft_download = 'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin'
    print(subprocess.check_output(f'wget -O /tmp/lid.176.bin {ft_download}'))

fmodel = fasttext.load_model('/tmp/lid.176.bin')

def fasttext_language(text):
    result = fmodel.predict(text)
    return result[0][0][-2:] if result else ''


# GCLD3 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import gcld3
gmodel = gcld3.NNetLanguageIdentifier(min_num_bytes=1, max_num_bytes=1000)

def gcld3_language(text):
    return gmodel.FindLanguage(text=text).language


# Lingua ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from lingua import Language, LanguageDetectorBuilder
lg = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()

def lingua_language(text):
    result = lg.detect_language_of(text)
    lg_mapping = {Language.CHINESE: 'zh',
                  Language.JAPANESE: 'ja',
                  Language.KOREAN: 'ko'}
    return lg_mapping[result] if result in lg_mapping else result


# Create test cases ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_last_names(lang):
    names = []
    with open(f'../../person-names/{lang}-surnames.txt', 'r') as f:
        names = f.read().splitlines()
    return names

# import importlib
# from faker.generator import Generator

# # Some values are tuples, some are strings.
# def name_part(value):
#     return value if isinstance(value, str) else value[0]

# def get_last_names(*locales):
#     last_names = []
#     for locale_name in locales:
#         module_name = f'faker.providers.person.{locale_name}'
#         faker_module = importlib.import_module(module_name, package=None)
#         provider = faker_module.Provider(Generator())
#         last_names_for_locale = getattr(provider, 'last_names', [])
#         last_names.extend(name_part(value) for value in last_names_for_locale)
#     return last_names

def compare_models(lang, last_names):
    fasttext_wrong = 0
    gcld3_wrong = 0
    lingua_wrong = 0
    consensus_wrong = 0

    print('----')
    for name in last_names:
        f_answer = fasttext_language(name)
        fasttext_wrong += (1 if f_answer != lang else 0)

        g_answer = gcld3_language(name)
        gcld3_wrong += (1 if g_answer != lang else 0)

        l_answer = lingua_language(name)
        lingua_wrong += (1 if l_answer != lang else 0)

        print(f'{name}: fasttext = {f_answer}, gcld3 = {g_answer}, lingua = {l_answer}')
        total_right = sum(answer == lang for answer in [f_answer, g_answer, l_answer])
        consensus_wrong += (1 if total_right < 2 else 0)

    print(f'fasttext errors: {fasttext_wrong}')
    print(f'gcld3 errors: {gcld3_wrong}')
    print(f'lingua errors: {lingua_wrong}')
    print(f'consensus wrong: {consensus_wrong}')
    print('')

# print('Japanese names:')
# compare_models('ja', get_last_names('ja_JP'))

# print('Korean names:')
# compare_models('ko', get_last_names('ko_KR'))

# print('Chinese names:')
# compare_models('zh', get_last_names('zh_TW', 'zh_CN'))

print('Japanese names:')
compare_models('ja', get_last_names('japanese'))

print('Korean names:')
compare_models('ko', get_last_names('korean'))

print('Chinese names:')
compare_models('zh', get_last_names('chinese'))


# for locale_name in ('zh_TW', 'zh_CN', 'ko_KR', 'ja_JP'):
#     module_name = f'faker.providers.person.{locale_name}'
#     faker_module = importlib.import_module(module_name, package=None)
#     provider = faker_module.Provider(Generator())
#     last_names_for_locale = getattr(provider, 'last_names', [])
#     last_names.extend(name_part(value) for value in last_names_for_locale)

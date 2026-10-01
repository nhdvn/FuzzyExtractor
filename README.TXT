
Requirement:
- Python + Numpy
- Golang


Normal Usage:
1. Get Template
    - python TemplateExtractor.py [action] [dataset] [userid] [number]

    Flag:
    - action: list, load, test
    - dataset: vkyc, timit
    - number: the amount of templates

    Example:
    - View All User In Dataset:
        - python TemplateExtractor.py list vkyc
        - python TemplateExtractor.py list timit

    - Save User Template To File:
        - python TemplateExtractor.py load vkyc 6 5
        - python TemplateExtractor.py load timit 5 3
        - Output File: [dataset]_[userid]_[number].txt


2. Using VoiceCryptoSystem (Python Version)
    - python VoiceCryptoSystem.py [action] [userid] [input]

    Flag
    - action: enroll, verify
    - userid: the identity to be used for the action
    - input: file path contains user template

    Example:
    - Enroll User:
        - python VoiceCryptoSystem.py enroll 1 vkyc_1_5.txt

    - Verify User:
        - python VoiceCryptoSystem.py verify 1 vkyc_1_3.txt




For Testing FAR and FRR: 
1. Get Data For Testing
    - python TemplateExtractor.py test [dataset] [uid_x] [number_x] [uid_y] [number_y]

    Flag: 
    - uid_x: the user id to get data for enroll
    - uid_y: the user id to get data for verify
    - number_x: the amount of templates for enroll
    - number_y: the amount of templates for verify

    Example:
    - python TemplateExtractor.py test timit 53 2 6 1
    - python TemplateExtractor.py test timit 5 2 5 1
    - Output File: test.txt (2 binary string to testing)


2. Using VoiceCryptoSystem (Go Version)
    - go run VoiceCryptoSystem.go
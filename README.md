# Sequence Generator based on XMEML generated from Adobe Premiere CC 2014 #

This repository presents commandline interface for generaning a lot of
XML files in format available to import back to Adobe Premiere.

Let's say your project inside Premiere have this structure:
`
├── 1___intro
│   ├── Step2from26
│   │   ├── Step2from26_Professor.TS
│   │   └── Step2from26_Screen.mp4
│   ├── Step3from26
│   │   ├── Step2from26_Professor.TS
│   │   └── Step2from26_Screen.mp4
│   ├── Step4from26
│   │   ├── Step2from26_Professor.TS
│   │   └── Step2from26_Screen.mp4
│   ├── Step5from26
│   │   ├── Step2from26_Professor.TS
│   │   └── Step2from26_Screen.mp4
`

First create Template sequence, inside any of Step_from_ folder, 
than run script with parameters:
`
python3 run.py (-template <path>) (-in <path>)  
`
and it will genrate a lot of XML sequences, for structure like:
`
├── 1___intro
│   ├── Step2from26
│   │   ├── Step2from26_Professor.TS
│   │   ├── Step2from26_seq
│   │   └── Step2from26_Screen.mp4
│   ├── Step3from26
│   │   ├── Step3from26_Professor.TS
│   │   ├── Step3from26_seq
│   │   └── Step3from26_Screen.mp4
│   ├── Step4from26
│   │   ├── Step4from26_Professor.TS
│   │   ├── Step4from26_seq
│   │   └── Step4from26_Screen.mp4
│   ├── Step5from26
│   │   ├── Step5from26_Professor.TS
│   │   ├── Step5from26_seq
│   │   └── Step5from26_Screen.mp4
`

just drag-and-drop them inside proper location inside Premiere and you are done.
Now you only need to make color correction and audio adjustmens! No more montage!

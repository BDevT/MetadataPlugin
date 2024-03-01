. ../venv/bin/activate

RUN=1

echo STEP 1 START
python cli_example.py step1 --kwargs run=$RUN

echo STEP 1 FINISHED
#exit 0

echo

echo STEP 2 START


python cli_example.py step2 --kwargs run=$RUN

echo STEP 2 FINISHED

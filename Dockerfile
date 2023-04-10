FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY src/common.py ${LAMBDA_TASK_ROOT}
COPY src/munros.py ${LAMBDA_TASK_ROOT}

CMD [ "munros.lambda_handler" ]

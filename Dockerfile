FROM continuumio/miniconda
MAINTAINER Kyle Horn

WORKDIR /app

# create the conda-based environment
RUN conda install --yes python=3 requests boto tqdm
RUN pip install bs4

COPY ./ /app/
ENTRYPOINT ["python","main.py"]

from setuptools import find_packages,setup
from typing import List
def get_requirements()->list[str]:
    requirements_list:list[str]=[]
    return  requirements_list

setup(
    name="Sensor",
    version="0.0.1",
    author="Shravan Kumar Pandey",
    author_email="shravankumarpandy825412@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements(),

)
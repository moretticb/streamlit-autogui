from pathlib import Path

import setuptools

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="streamlit-autogui",
    version="0.0.4",
    author="Caio Benatti Moretti",
    author_email="caiodba@gmail.com ",
    description="Vibe code inside a streamlit application and prompt for features on the fly.",
    long_description="Vibe code inside a streamlit application and prompt for technical implementations coupled with GUI components on the fly. Give tweaks on top of the generated code if needed.",
    long_description_content_type="text/plain",
    url="https://github.com/moretticb/streamlit-autogui",
    packages=setuptools.find_namespace_packages(),
#    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.7",
    install_requires=[
        "streamlit >= 0.63",
        "openai >= 2.6.1",
        "aisuite >= 0.1.13",
        "streamlit-code-editor >= 0.1.22"
    ],
    extras_require={
        "devel": [
            "wheel",
            "pytest==7.4.0",
            "playwright==1.48.0",
            "requests==2.31.0",
            "pytest-playwright-snapshot==1.0",
            "pytest-rerunfailures==12.0",
        ]
    }
)

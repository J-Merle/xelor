from setuptools import find_packages, setup

setup(
    name="xelor",
    version="0.1",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=["Click"],
    entry_points="""
        [console_scripts]
        xelor=xelor.app:cli""",
)

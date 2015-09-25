from setuptools import setup


setup(
    name="clitube",
    version="0.0.1",
    author="NiZiL",
    description=("Browse and listen Youtube's video from your terminal"),

    packages=['clitube'],
    scripts=['scripts/clitube'],

    install_requires=['requests', 'youtube-dl']
)

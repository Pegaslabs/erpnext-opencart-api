from setuptools import setup, find_packages

version = '0.0.1'

setup(
    name='opencart_api',
    version=version,
    description='App for connecting Opencart through APIs.',
    author='olhonko@gmail.com',
    author_email='olhonko@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)

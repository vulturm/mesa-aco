%global build_branch master
%global pkg_name lldb

%global build_repo https://github.com/llvm-mirror/%{pkg_name}

%global maj_ver %(curl -s https://raw.githubusercontent.com/llvm/llvm-project/%{build_branch}/llvm/CMakeLists.txt | grep LLVM_VERSION_MAJOR | grep -oP '[0-9]+')
%global min_ver %(curl -s https://raw.githubusercontent.com/llvm/llvm-project/%{build_branch}/llvm/CMakeLists.txt | grep LLVM_VERSION_MINOR | grep -oP '[0-9]+')
%global patch_ver %(curl -s https://raw.githubusercontent.com/llvm/llvm-project/%{build_branch}/llvm/CMakeLists.txt | grep LLVM_VERSION_PATCH | grep -oP '[0-9]+')

%define commit %(git ls-remote %{build_repo} | grep -w "refs/heads/%{build_branch}" | awk '{print $1}')
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global commit_date %(date +"%Y%m%d.%H")
%global gitrel .%{commit_date}.git%{shortcommit}


Name:		%{pkg_name}
Version:	%{maj_ver}.%{min_ver}.%{patch_ver}
Release:	0.1%{?gitrel}%{?dist}
Summary:	Next generation high-performance debugger

License:	NCSA
URL:		https://github.com/llvm-mirror/
Source0:	%url/%{name}/archive/%{build_branch}.tar.gz#/%{name}-%{build_branch}.tar.gz


BuildRequires:	cmake
BuildRequires:	llvm-devel = %{version}
BuildRequires:	llvm-test = %{version}
BuildRequires:	clang-devel = %{version}
BuildRequires:	ncurses-devel
BuildRequires:	swig
BuildRequires:	llvm-static = %{version}
BuildRequires:	libffi-devel
BuildRequires:	zlib-devel
BuildRequires:	libxml2-devel
BuildRequires:	libedit-devel
BuildRequires:	python2-lit

Requires:	python2-lldb

%description
LLDB is a next generation, high-performance debugger. It is built as a set
of reusable components which highly leverage existing libraries in the
larger LLVM Project, such as the Clang expression parser and LLVM
disassembler.

%package devel
Summary:	Development header files for LLDB
Requires:	%{name}%{?_isa} = %{version}-%{release}

%description devel
The package contains header files for the LLDB debugger.

%package -n python2-lldb
%{?python_provide:%python_provide python2-lldb}
Summary:	Python module for LLDB
BuildRequires:	python2-devel
Requires:	python2-six

%description -n python2-lldb
The package contains the LLDB Python module.

%prep

%setup -q -n %{name}-%{build_branch}


# HACK so that lldb can find its custom readline.so, because we move it
# after install.
sed -i -e "s~import sys~import sys\nsys.path.insert\(1, '%{python2_sitearch}/lldb'\)~g" source/Interpreter/embedded_interpreter.py

%build

mkdir -p _build
cd _build

# Python version detection is broken

LDFLAGS="%{__global_ldflags} -lpthread -ldl"

CFLAGS="%{optflags} -Wno-error=format-security"
CXXFLAGS="%{optflags} -Wno-error=format-security"

%cmake .. \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_CONFIG:FILEPATH=/usr/bin/llvm-config-%{__isa_bits} \
	\
	-DLLDB_DISABLE_CURSES:BOOL=OFF \
	-DLLDB_DISABLE_LIBEDIT:BOOL=OFF \
	-DLLDB_DISABLE_PYTHON:BOOL=OFF \
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
	\
	-DPYTHON_EXECUTABLE:STRING=%{__python2} \
	-DPYTHON_VERSION_MAJOR:STRING=$(%{__python2} -c "import sys; print(sys.version_info.major)") \
	-DPYTHON_VERSION_MINOR:STRING=$(%{__python2} -c "import sys; print(sys.version_info.minor)") \
	-DLLVM_EXTERNAL_LIT=%{_bindir}/lit \
	-DLLVM_LIT_ARGS="-sv \
	--path %{_libdir}/llvm" \

make %{?_smp_mflags}

%install
cd _build
make install DESTDIR=%{buildroot}

# remove static libraries
rm -fv %{buildroot}%{_libdir}/*.a

# python: fix binary libraries location
liblldb=$(basename $(readlink -e %{buildroot}%{_libdir}/liblldb.so))
ln -vsf "../../../${liblldb}" %{buildroot}%{python2_sitearch}/lldb/_lldb.so
#mv -v %{buildroot}%{python2_sitearch}/readline.so %{buildroot}%{python2_sitearch}/lldb/readline.so
%py_byte_compile %{__python2} %{buildroot}%{python2_sitearch}/lldb

# remove bundled six.py
rm -f %{buildroot}%{python2_sitearch}/six.*

%ldconfig_scriptlets

%files
%{_bindir}/lldb*
%{_libdir}/liblldb.so.*
%{_libdir}/liblldbIntelFeatures.so.*

%files devel
%{_includedir}/lldb
%{_libdir}/*.so

%files -n python2-lldb
%{python2_sitearch}/lldb

%changelog
* Sun Jul 14 2019 Mihai Vultur <xanto@egaming.ro>
- Implement some version autodetection to reduce maintenance work. 


# Statistics computed for the SuiteSparse Matrix Collection

[Statistics computed for the University of Florida Sparse Matrix Collection](https://www.cise.ufl.edu/research/sparse/matrices/stats.html)

> **NOTE**: A CSV file is also available with some of this index information (UFstats.csv). The first line of the CSV file gives the number of matrices in the collection, and the second line gives the LastRevisionDate. Line k+2 in the file lists the following statistics for the matrix whose id number is k: Group, Name, nrows, ncols, nnz, isReal, isBinary, isND, posdef, pattern_symmetry, numerical_symmetry, and kind.

The index for the UF Collection contains a set of statistics about each matrix in the collection. A table of these statistics can be loaded into MATLAB via index=UFget, and by list=UFkinds. Below is a summary of what they are and how they are computed. The first two are for the whole collection, and the rest are statistics for each matrix.

LastRevisionDate
    This is a single string kept in the UF_index MATLAB struct that states when the collection or the index was last modified.
DownloadTimeStamp
    The date and time the index that you last downloaded the index.
Group
    A cell array. Group{id} is the group name for the matrix whose serial number is 'id'. Each matrix has a unique id number in the range of 1 to the number of matrices in the collection. Once an id is assigned to a matrix, it never changes.
Name
    Name{id} is the name of the matrix (excluding the Group). Name{id} is not unique. The full name of a matrix should always be given as Group/Name.
nrows
    The number of rows in the matrix.
ncols
    The number of columns in the matrix.
nnz
    The number of numerically nonzero entries in the matrix, or nnz(Problem.A) in MATLAB, where Problem=UFget(id) is a struct containing the MATLAB format of the problem. This statistic can differ from the number of 'entries' explicitly stored in the matrix, however, since some of these entries may be numerically zero. In the MATLAB format, these explicit zero entries are stored in the binary Problem.Zeros matrix, since MATLAB drops all explicit zeros from its sparse matrix storage. The Problem.A matrix in MATLAB has nnz entries in it, with no explicit zeros. In the Matrix Market and Rutherford-Boeing format, a single file holds all entries, both nonzero and the explicit zero entries.
nzero
    The number of explicit entries present in the matrix that are provided by the matrix author but which are numerically zero. nzero(id) is nnz(Problem.Zeros).
pattern_symmetry
    Let S=spones(Problem.A) be the binary pattern of the explicit nonzeros in the matrix. Let pmatched be the number of matched offdiagonal entries, where both S(i,j) and S(j,i) are one, with i not equal to j. Let nzoffdiag be the number of offdiagonal entries in S. Then pattern_symmetry is the ratio of pmatched/nzoffdiag. Note that if S(i,j) and S(j,i) are both one, then this pair of entries is counted twice in both pmatched and nzoffdiag. If the matrix is rectangular, this statistic is zero. If there are no offdiagonal entries, the statistic is 1.
numerical_symmetry
    Let xmatched be the number of matched offdiagonal entries, where A(i,j) is equal to the complex conjugate of A(j,i) and where i and j are not equal. Then numerical_symmetry is the ration xmatched / nzoffdiag (or 1 if nzoffdiag is zero). This statistic is zero for rectangular matrices. Note that this statistic measures how close a matrix is to being Hermitian (A=A' in MATLAB). For complex symmetric matrices (A=A.' in MATLAB), this ratio will be less than one (unless all offdiagonal entries are real).
isBinary
    1 if the matrix is binary (all entries are 0 or 1), 0 otherwise.
isReal
    1 if the matrix is real, 0 if complex.
nnzdiag
    The number of numerically nonzero entries on the diagonal (nnz (diag (Problem.A)) in MATLAB notation). This statistic ignores explicit zero entries (Problem.Zeros in the MATLAB struct).
posdef
    1 if the matrix is known to be symmetric positive definite (or Hermitian positive definite for the complex case), 0 if it is known not to be, -1 if it is symmetric (or Hermitian) but with unknown positive-definiteness. If the statistic is unknown (-1) this may be revised in subsequent versions of the index.
amd_lnz
    Let C=S+S' where S=spones(A) is the binary pattern of A. Then amd_lnz is number of nonzeros in the Cholesky factorization of the matrix C(p,p) (assuming C is positive definite) where p=amd(C) is the AMD fill-reducing ordering. This statistic is -2 for rectangular matrices or for graph problems. It is -1 if it is not computed. This figure gives an estimate of the memory requirements for x=A\b in MATLAB for square matrices.
amd_flops
    The floating-point operation count for computing the Cholesky factorization of C(p,p) (see above).
amd_vnz
    The number of entries in a Householder-vector representation of the Q factor of R (but not the QR in MATLAB), after a COLAMD fill-reducing ordering. This is an upper bound on L for the LU factorization of A.
amd_rnz
    The number of entries in R for the QR factorization of A, after a COLAMD fill-reducing ordering. This is an upper bound on U for the LU factorization of A.
nblocks
    The number of blocks from dmperm (see dmperm in MATLAB).
sprank
    The structural rank of the matrix, which is the number of maximual number of nonzero entries that can be permuted to the diagonal (see dmperm, or sprank in MATLAB). This statistic is not computed for problems that represent graphs, since in those cases the diagonal of the matrix is often not relevant (self-edges are often ignored).
RBtype
    The Rutherford Boeing type of the matrix (ignoring explicit zeros in Problem.Zeros). RBtype is a a 3-letter lower-case string. The first letter is:

    r
        if A is real but not binary
    p
        if A is binary
    c
        if A is complex
    i
        if A is integer

    The second letter:

    r
        if A is rectangular
    u
        if A is square and unsymmetric
    s
        if A is symmetric (nnz(A-A.') is zero in MATLAB)
    h
        if A is Hermitian (nnz(A-A') is zero in MATLAB)
    z
        if A is skew-symmetric (nnz(A+A.') is zero in MATLAB)

    The third letter is always 'a' (for 'assembled'). The RB format allows for unassembled finite-element matrices, but they are converted to assembled format for this collection.
cholcand
    1 if the matrix is symmetric (Hermitian if complex) and if all the diagonal entries are postive and real. Zero otherwise. If 1, the matrix is a candidate for a Cholesky factorization, which MATLAB will first try when computing x=A\b.
ncc
    The number of of strongly-connected components in the graph of A (if A is square) or in the bipartite graph if A is rectangular. The diagonal is ignored.
isND
    1 if the problem comes from a 2D/3D discretization, zero otherwise. This determination is not a property of the matrix, but a qualitative assesment of the kind of problem the matrix represents.
isGraph
    1 if the problem is best considered as a graph rather than a system of equations, zero otherwise. This determination is not a property of the matrix, but a qualitative assesment of the kind of problem the matrix represents.

UFstats.csv

A CSV file is also available with some of this index information (UFstats.csv). The first line of the CSV file gives the number of matrices in the collection, and the second line gives the LastRevisionDate. Line k+2 in the file lists the following statistics for the matrix whose id number is k: Group, Name, nrows, ncols, nnz, isReal, isBinary, isND, posdef, pattern_symmetry, numerical_symmetry, and kind.
SVD-based statistics

The following statistics are not (yet) in the UFindex. They are currently available only on the web page for each matrix. You can also download the singular values at www.cise.ufl.edu/research/sparse/svd. These were typically calculated with s=svd(full(A)) in MATLAB, are are thus only available for modest-sized matrices.

norm(A)
    The 2-norm of A (the largest singular value)
min(svd(A))
    The smallest singular value
cond(A)
    The 2-norm condition number, which is the ratio of the largest over the smallest singular value.
rank(A)
    The rank of the matrix, which is the number of singular values larger than the tolerance of max(m,n)*eps(norm(A)). This tolerance is plotted in green in the figure.
sprank(A)-rank(A)
    sprank(A) (see above) is an upper bound on the rank of A.
null space dimension
    The dimension of the null space (zero if it has full numerical rank). This is simply min(m,n)-rank(A).
full numerical rank?
    'yes' or 'no'.
singular value gap
    If k=rank(A), and the matrix is rank deficient, then this is the ratio s(k)/s(k+1). A red line between the kth and (k+1)st singular value is drawn to illustrate this gap.
singular values
    These can be downloaded as a MATLAB MAT-file. Each file contains a struct with the fields: s (a vector containing the singular values), how (a string stating how the SVD was computed), and status (a string that is either 'ok' or a warning). If the status shows that the SVD did not converge, the singular values are probably not computed accurately.

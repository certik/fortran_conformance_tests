! rule: S7.5.10-009
! covers: allocated-source-bounds-values, nonallocatable-whole-array-source, ordinary-scalar-conversion
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
program structure_constructor_7_5_10_b_alloc_matrix
implicit none
type :: box
  integer, allocatable :: from_alloc(:)
  integer, allocatable :: from_ordinary(:)
  integer, allocatable :: scalar
end type box
integer, allocatable :: source(:)
integer :: ordinary(-2:0)
real :: scalar_source
allocate(source(-2:0))
source(-2)=11
source(-1)=13
source(0)=17
ordinary(-2)=21
ordinary(-1)=23
ordinary(0)=27
scalar_source = 4.0
call observe(box(from_alloc=source, from_ordinary=ordinary, scalar=scalar_source))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR ALLOCATABLE SOURCE MATRIX OK'
contains
subroutine observe(x)
  type(box), intent(in) :: x
  if (.not. allocated(x%from_alloc)) error stop 1
  if (lbound(x%from_alloc,1) /= -2) error stop 2
  if (ubound(x%from_alloc,1) /= 0) error stop 3
  if (x%from_alloc(-1) /= 13) error stop 4
  if (.not. allocated(x%from_ordinary)) error stop 5
  if (lbound(x%from_ordinary,1) /= -2) error stop 6
  if (x%from_ordinary(-1) /= 23) error stop 7
  if (.not. allocated(x%scalar)) error stop 8
  if (x%scalar /= 4) error stop 9
end subroutine observe
end program structure_constructor_7_5_10_b_alloc_matrix

! rule: S7.5.10-008
! covers: same-rank-allocatable-source-use, same-rank-other-source-use
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
program structure_constructor_7_5_10_b_same_rank_sources
implicit none
type :: box
  integer, allocatable :: from_alloc(:)
  integer, allocatable :: from_ordinary(:)
end type box
integer, allocatable :: source(:)
integer :: ordinary(-2:0)
allocate(source(-2:0))
source(-2)=11
source(-1)=13
source(0)=17
ordinary(-2)=21
ordinary(-1)=23
ordinary(0)=27
call observe(box(from_alloc=source, from_ordinary=ordinary))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR ALLOCATABLE SAME RANK SOURCES OK'
contains
subroutine observe(x)
  type(box), intent(in) :: x
  if (.not. allocated(x%from_alloc)) error stop 1
  if (lbound(x%from_alloc,1) /= -2) error stop 2
  if (x%from_alloc(-1) /= 13) error stop 3
  if (.not. allocated(x%from_ordinary)) error stop 4
  if (lbound(x%from_ordinary,1) /= -2) error stop 5
  if (x%from_ordinary(-1) /= 23) error stop 6
end subroutine observe
end program structure_constructor_7_5_10_b_same_rank_sources

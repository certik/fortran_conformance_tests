! rule: S7.5.10-008
! covers: no-mold-null-unallocated
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_no_mold_null_allocatable_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer, allocatable :: scalar
    integer, allocatable :: vector(:)
  end type record
  checks=0
  call observe(record(101, 103, scalar=null(), vector=null()))
  if (checks /= 5) then
    write(*,'(a)') 'DTSC:no_mold_null_allocatable:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR NO MOLD NULL ALLOCATABLE OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:no_mold_null_allocatable:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:no_mold_null_allocatable:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:no_mold_null_allocatable:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. allocated(obj%scalar))) then
      write(*,'(a)') 'DTSC:no_mold_null_allocatable:scalar-null-unallocated'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. allocated(obj%vector))) then
      write(*,'(a)') 'DTSC:no_mold_null_allocatable:vector-null-unallocated'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_no_mold_null_allocatable_effect

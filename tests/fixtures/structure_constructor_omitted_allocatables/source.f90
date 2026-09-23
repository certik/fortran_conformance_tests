! rule: S7.5.10-005
! covers: omitted-allocatable-status
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_omitted_allocatables_effect
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
  call observe(record(101, 103))
  if (checks /= 5) then
    write(*,'(a)') 'DTSC:omitted_allocatables:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR OMITTED ALLOCATABLES OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:omitted_allocatables:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:omitted_allocatables:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:omitted_allocatables:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. allocated(obj%scalar))) then
      write(*,'(a)') 'DTSC:omitted_allocatables:scalar-unallocated'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. allocated(obj%vector))) then
      write(*,'(a)') 'DTSC:omitted_allocatables:vector-unallocated'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_omitted_allocatables_effect

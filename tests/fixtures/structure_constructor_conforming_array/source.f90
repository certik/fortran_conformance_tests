! rule: S7.5.10-004
! covers: conforming-array-value
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_conforming_array_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: values(-1:1)
  end type record
  integer :: source(3)
  checks=0
  source(1)=11
  source(2)=13
  source(3)=17
  call observe(record(101, 103, values=source))
  if (checks /= 8) then
    write(*,'(a)') 'DTSC:conforming_array:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR CONFORMING ARRAY OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:conforming_array:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:conforming_array:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:conforming_array:default-stamp'
      error stop
    end if
    checks=checks+1
    if (lbound(obj%values,1) /= -1) then
      write(*,'(a)') 'DTSC:conforming_array:array-lbound'
      error stop
    end if
    checks=checks+1
    if (ubound(obj%values,1) /= 1) then
      write(*,'(a)') 'DTSC:conforming_array:array-ubound'
      error stop
    end if
    checks=checks+1
    if (obj%values(-1) /= 11) then
      write(*,'(a)') 'DTSC:conforming_array:conforming-value--1'
      error stop
    end if
    checks=checks+1
    if (obj%values(0) /= 13) then
      write(*,'(a)') 'DTSC:conforming_array:conforming-value-0'
      error stop
    end if
    checks=checks+1
    if (obj%values(1) /= 17) then
      write(*,'(a)') 'DTSC:conforming_array:conforming-value-1'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_conforming_array_effect

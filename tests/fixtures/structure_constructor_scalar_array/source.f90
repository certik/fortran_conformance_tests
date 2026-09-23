! rule: S7.5.10-004
! covers: scalar-to-ordinary-array
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_scalar_array_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: values(-1:1)
  end type record
  integer :: scalar
  checks=0
  scalar=17
  call observe(record(101, 103, values=scalar))
  if (checks /= 8) then
    write(*,'(a)') 'DTSC:scalar_array:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR SCALAR ARRAY OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:scalar_array:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:scalar_array:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:scalar_array:default-stamp'
      error stop
    end if
    checks=checks+1
    if (lbound(obj%values,1) /= -1) then
      write(*,'(a)') 'DTSC:scalar_array:array-lbound'
      error stop
    end if
    checks=checks+1
    if (ubound(obj%values,1) /= 1) then
      write(*,'(a)') 'DTSC:scalar_array:array-ubound'
      error stop
    end if
    checks=checks+1
    if (obj%values(-1) /= 17) then
      write(*,'(a)') 'DTSC:scalar_array:scalar-expanded--1'
      error stop
    end if
    checks=checks+1
    if (obj%values(0) /= 17) then
      write(*,'(a)') 'DTSC:scalar_array:scalar-expanded-0'
      error stop
    end if
    checks=checks+1
    if (obj%values(1) /= 17) then
      write(*,'(a)') 'DTSC:scalar_array:scalar-expanded-1'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_scalar_array_effect

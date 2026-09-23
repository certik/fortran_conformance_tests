! rule: S7.5.10-003
! covers: numeric-conversion
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_numeric_conversion_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: value
  end type record
  real :: source
  checks=0
  source=4.0
  call observe(record(101, 103, value=source))
  if (checks /= 4) then
    write(*,'(a)') 'DTSC:numeric_conversion:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR NUMERIC CONVERSION OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:numeric_conversion:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:numeric_conversion:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:numeric_conversion:default-stamp'
      error stop
    end if
    checks=checks+1
    if (obj%value /= 4) then
      write(*,'(a)') 'DTSC:numeric_conversion:converted-integer'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_numeric_conversion_effect

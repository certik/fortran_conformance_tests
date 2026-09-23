! rule: S7.5.10-001
! covers: array-component-not-elemental-constructor
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_array_component_scalar_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: values(3)
  end type record
  integer :: source(3)
  checks=0
  source(1)=11
  source(2)=13
  source(3)=17
  call observe(record(101, 103, values=source))
  if (checks /= 6) then
    write(*,'(a)') 'DTSC:array_component_scalar:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR ARRAY COMPONENT SCALAR OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:array_component_scalar:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:array_component_scalar:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:array_component_scalar:default-stamp'
      error stop
    end if
    checks=checks+1
    if (obj%values(1) /= 11) then
      write(*,'(a)') 'DTSC:array_component_scalar:array-value-1'
      error stop
    end if
    checks=checks+1
    if (obj%values(2) /= 13) then
      write(*,'(a)') 'DTSC:array_component_scalar:array-value-2'
      error stop
    end if
    checks=checks+1
    if (obj%values(3) /= 17) then
      write(*,'(a)') 'DTSC:array_component_scalar:array-value-3'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_array_component_scalar_effect

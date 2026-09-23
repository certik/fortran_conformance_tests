! rule: S7.5.10-005
! covers: omitted-value-default
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_omitted_defaults_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer :: left = 11
    integer :: right = 13
  end type record
  checks=0
  call observe_default(record(101, 103))
  call observe_override(record(101, 103, right=29))
  if (checks /= 7) then
    write(*,'(a)') 'DTSC:omitted_defaults:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR OMITTED DEFAULTS OK'
contains
  subroutine observe_default(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:omitted_defaults:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:omitted_defaults:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:omitted_defaults:default-stamp'
      error stop
    end if
    checks=checks+1
    if (obj%left /= 11) then
      write(*,'(a)') 'DTSC:omitted_defaults:default-left'
      error stop
    end if
    checks=checks+1
    if (obj%right /= 13) then
      write(*,'(a)') 'DTSC:omitted_defaults:default-right'
      error stop
    end if
    checks=checks+1
  end subroutine observe_default
  subroutine observe_override(obj)
    type(record), intent(in) :: obj
    if (obj%left /= 11) then
      write(*,'(a)') 'DTSC:omitted_defaults:override-left-default'
      error stop
    end if
    checks=checks+1
    if (obj%right /= 29) then
      write(*,'(a)') 'DTSC:omitted_defaults:override-right'
      error stop
    end if
    checks=checks+1
  end subroutine observe_override
end program structure_constructor_omitted_defaults_effect

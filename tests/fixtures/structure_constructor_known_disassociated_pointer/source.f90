! rule: S7.5.10-007
! covers: known-disassociated-pointer
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_known_disassociated_pointer_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer, pointer :: p
  end type record
  integer, target :: target
  integer, pointer :: source
  checks=0
  target=17
  source => null()
  call observe(record(101, 103, p=source))
  if (checks /= 4) then
    write(*,'(a)') 'DTSC:known_disassociated_pointer:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR KNOWN DISASSOCIATED POINTER OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:known_disassociated_pointer:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:known_disassociated_pointer:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:known_disassociated_pointer:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. associated(obj%p))) then
      write(*,'(a)') 'DTSC:known_disassociated_pointer:component-disassociated'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_known_disassociated_pointer_effect

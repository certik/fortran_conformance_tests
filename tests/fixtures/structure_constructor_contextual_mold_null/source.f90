! rule: S7.5.10-007
! covers: contextual-and-mold-null
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_contextual_mold_null_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer, pointer :: p(:)
    integer, pointer :: q(:)
  end type record
  integer, target :: target(3)
  integer, pointer :: mold(:)
  checks=0
  target=[11,13,17]
  mold => null()
  call observe(record(101, 103, p=null(), q=null(mold=mold)))
  if (checks /= 5) then
    write(*,'(a)') 'DTSC:contextual_mold_null:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR CONTEXTUAL MOLD NULL OK'
contains
  subroutine observe(obj)
    type(record), intent(in) :: obj
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:contextual_mold_null:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:contextual_mold_null:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:contextual_mold_null:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. associated(obj%p))) then
      write(*,'(a)') 'DTSC:contextual_mold_null:null-component-disassociated'
      error stop
    end if
    checks=checks+1
    if (.not. (.not. associated(obj%q))) then
      write(*,'(a)') 'DTSC:contextual_mold_null:mold-null-component-disassociated'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_contextual_mold_null_effect

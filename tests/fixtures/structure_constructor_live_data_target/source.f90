! rule: S7.5.10-007
! covers: live-data-target-alias
! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.
! Each source has a nonzero default component plus positional controls for feature mutation.
program structure_constructor_live_data_target_effect
  implicit none
  integer :: checks
  type :: record
    integer :: lead
    integer :: swapped
    integer :: stamp = -9051
    integer, pointer :: p
  end type record
  checks=0
  call worker()
  if (checks /= 5) then
    write(*,'(a)') 'DTSC:live_data_target:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE CONSTRUCTOR LIVE DATA TARGET OK'
contains
  subroutine worker()
    integer, target :: datum
    datum=17
    call observe(record(101, 103, p=datum), datum)
  end subroutine worker
  subroutine observe(obj, datum)
    type(record), intent(in) :: obj
    integer, target, intent(in) :: datum
    if (obj%lead /= 101) then
      write(*,'(a)') 'DTSC:live_data_target:lead-component'
      error stop
    end if
    checks=checks+1
    if (obj%swapped /= 103) then
      write(*,'(a)') 'DTSC:live_data_target:swapped-component'
      error stop
    end if
    checks=checks+1
    if (obj%stamp /= -9051) then
      write(*,'(a)') 'DTSC:live_data_target:default-stamp'
      error stop
    end if
    checks=checks+1
    if (.not. (associated(obj%p, datum))) then
      write(*,'(a)') 'DTSC:live_data_target:associated-with-live-target'
      error stop
    end if
    checks=checks+1
    if (obj%p /= 17) then
      write(*,'(a)') 'DTSC:live_data_target:target-value-through-pointer'
      error stop
    end if
    checks=checks+1
  end subroutine observe
end program structure_constructor_live_data_target_effect

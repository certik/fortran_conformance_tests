! rule: S8.4-004
! covers: saved-scalar-target
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_saved_scalar_target_effect
  implicit none
  integer, target, save :: target_value = -22231
  integer, pointer :: p => target_value
  integer :: checks
  checks=0
  if (.not. associated(p, target_value)) then
    write(*,'(a)') 'INIT:saved_scalar_target:associated-with-target'
    error stop
  end if
  checks=checks+1
  if (p /= -22231) then
    write(*,'(a)') 'INIT:saved_scalar_target:initial-target-value'
    error stop
  end if
  checks=checks+1
  target_value = -22230
  if (p /= -22230) then
    write(*,'(a)') 'INIT:saved_scalar_target:updated-target-visible-through-pointer'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'INIT:saved_scalar_target:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION SAVED SCALAR TARGET OK'
end program initialization_saved_scalar_target_effect

! rule: S19.4-008
! covers: local-local-init-scope-of-do-concurrent
program scoping_19_3_19_5_local_scope
  implicit none
  integer :: checks
  integer :: i, local_value, init_value, observed(1)
  checks = 0
  local_value = -222
  init_value = 7
  observed = -333
  do concurrent (i = 1:1) local(local_value) local_init(init_value) shared(observed)
    local_value = 100
    observed(i) = local_value + init_value
    init_value = -77
  end do
  if (observed(1) /= 107) then
    write(*,'(a)') 'SCOPE:local_scope:local-result'
    error stop
  end if
  checks = checks + 1
  if (local_value /= -222) then
    write(*,'(a)') 'SCOPE:local_scope:local-outer'
    error stop
  end if
  checks = checks + 1
  if (init_value /= 7) then
    write(*,'(a)') 'SCOPE:local_scope:local-init-outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'SCOPE:local_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 LOCAL SCOPE OK'
contains
end program scoping_19_3_19_5_local_scope

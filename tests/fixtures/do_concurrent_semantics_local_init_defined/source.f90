! rule: S11.1.7.5-003
! covers: local-initial-undefined-source-control
! covers: local-assigned-before-use-control
! covers: local-init-copies-outside-definition-status
! covers: local-init-outside-defined-source-control
program do_concurrent_semantics_local_init_defined
  implicit none
  integer :: checks
  integer :: i
  integer :: local_value, init_value
  integer :: observed(1)
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
    write(*,'(a)') 'DCS:local_init_defined:local-init-copy'
    error stop
  end if
  checks = checks + 1
  if (local_value /= -222) then
    write(*,'(a)') 'DCS:local_init_defined:local-outside'
    error stop
  end if
  checks = checks + 1
  if (init_value /= 7) then
    write(*,'(a)') 'DCS:local_init_defined:local-init-outside'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'DCS:local_init_defined:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS LOCAL INIT DEFINED OK'
end program do_concurrent_semantics_local_init_defined

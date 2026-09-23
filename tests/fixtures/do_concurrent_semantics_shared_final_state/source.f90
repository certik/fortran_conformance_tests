! rule: S11.1.7.5-010
! covers: shared-refers-to-outside-final-state
! covers: shared-cross-iteration-definition-source-control
program do_concurrent_semantics_shared_final_state
  implicit none
  integer :: checks
  integer :: i
  integer :: shared_value
  checks = 0
  shared_value = -777
  do concurrent (i = 1:1) shared(shared_value)
    shared_value = 411
  end do
  if (shared_value /= 411) then
    write(*,'(a)') 'DCS:shared_final_state:outside-value'
    error stop
  end if
  checks = checks + 1
  if (checks /= 1) then
    write(*,'(a)') 'DCS:shared_final_state:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS SHARED FINAL STATE OK'
end program do_concurrent_semantics_shared_final_state

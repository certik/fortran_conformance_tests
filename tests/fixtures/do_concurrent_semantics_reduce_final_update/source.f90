! rule: S11.1.7.5-008
! covers: reduce-final-integer-result
! covers: reduce-outside-updated-only-at-termination
program do_concurrent_semantics_reduce_final_update
  implicit none
  integer :: checks
  integer :: i
  integer :: total_value
  checks = 0
  total_value = 100
  do concurrent (i = 1:4) reduce(+:total_value)
    total_value = total_value + i
  end do
  if (total_value /= 110) then
    write(*,'(a)') 'DCS:reduce_final_update:final-update'
    error stop
  end if
  checks = checks + 1
  if (checks /= 1) then
    write(*,'(a)') 'DCS:reduce_final_update:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE FINAL UPDATE OK'
end program do_concurrent_semantics_reduce_final_update

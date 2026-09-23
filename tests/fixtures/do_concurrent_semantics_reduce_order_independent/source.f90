! rule: S11.1.7.5-009
! covers: reduce-combination-order-unobservable-source-control
! covers: floating-reduce-order-sensitive-oracle-excluded
program do_concurrent_semantics_reduce_order_independent
  implicit none
  integer :: checks
  integer :: i
  integer :: total_value, maximum_value
  checks = 0
  total_value = 70
  maximum_value = -30
  do concurrent (i = 1:4) reduce(+:total_value) reduce(max:maximum_value)
    total_value = total_value + i
    maximum_value = max(maximum_value, 5 * i)
  end do
  if (total_value /= 80) then
    write(*,'(a)') 'DCS:reduce_order_independent:integer-sum'
    error stop
  end if
  checks = checks + 1
  if (maximum_value /= 20) then
    write(*,'(a)') 'DCS:reduce_order_independent:integer-max'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'DCS:reduce_order_independent:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE ORDER INDEPENDENT OK'
end program do_concurrent_semantics_reduce_order_independent

! rule: S11.1.7.5-007
! covers: reduce-variable-allowed-binary-left-form-control
! covers: reduce-variable-allowed-binary-right-form-control
! covers: reduce-variable-allowed-function-form-control
! covers: reduce-variable-same-form-source-control
program do_concurrent_semantics_reduce_forms
  implicit none
  integer :: checks
  integer :: i
  integer :: left_value, right_value, function_value
  checks = 0
  left_value = 10
  right_value = 10
  function_value = -5
  do concurrent (i = 1:3) reduce(+:left_value)
    left_value = left_value + i
  end do
  do concurrent (i = 1:3) reduce(+:right_value)
    right_value = i + right_value
  end do
  do concurrent (i = 1:3) reduce(max:function_value)
    function_value = max(i * 4, function_value)
  end do
  if (left_value /= 16) then
    write(*,'(a)') 'DCS:reduce_forms:left-form'
    error stop
  end if
  checks = checks + 1
  if (right_value /= 16) then
    write(*,'(a)') 'DCS:reduce_forms:right-form'
    error stop
  end if
  checks = checks + 1
  if (function_value /= 12) then
    write(*,'(a)') 'DCS:reduce_forms:function-form'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'DCS:reduce_forms:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE FORMS OK'
end program do_concurrent_semantics_reduce_forms

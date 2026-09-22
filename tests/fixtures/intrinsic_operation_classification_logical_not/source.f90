! rule: S10.1.5.1-005
! covers: logical-not
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_logical_not
  implicit none
  integer :: checks
  logical :: false_value, true_value, result_false, result_true
  checks=0
  false_value = .false.
  true_value = .true.
  ! .NOT. is checked on both logical input values: false -> true and true -> false.
  result_false = .not. false_value
  result_true = .not. true_value
  if (result_false) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_not:not-false-is-true'
    error stop
  end if
  if (result_true) then
    write(*,'(a)') 'IOC:logical_not:not-true-is-false'
    error stop
  else
  checks=checks+1
  end if
  if (checks /= 2) then
    write(*,'(a)') 'IOC:logical_not:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION LOGICAL NOT OK'
end program ioc_logical_not

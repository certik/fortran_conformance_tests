! rule: S10.1.5.1-005
! covers: logical-and
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_logical_and
  implicit none
  integer :: checks
  logical :: t, f, result_tt, result_tf, result_ft, result_ff
  checks=0
  t = .true.
  f = .false.
  ! Complete .AND. truth table: only true and true gives true.
  result_tt = t .and. t
  result_tf = t .and. f
  result_ft = f .and. t
  result_ff = f .and. f
  if (result_tt) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_and:and-true-true'
    error stop
  end if
  if (result_tf) then
    write(*,'(a)') 'IOC:logical_and:and-true-false'
    error stop
  else
  checks=checks+1
  end if
  if (result_ft) then
    write(*,'(a)') 'IOC:logical_and:and-false-true'
    error stop
  else
  checks=checks+1
  end if
  if (result_ff) then
    write(*,'(a)') 'IOC:logical_and:and-false-false'
    error stop
  else
  checks=checks+1
  end if
  if (checks /= 4) then
    write(*,'(a)') 'IOC:logical_and:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION LOGICAL AND OK'
end program ioc_logical_and

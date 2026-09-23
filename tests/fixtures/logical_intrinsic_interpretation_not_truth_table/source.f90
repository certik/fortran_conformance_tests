program lio_not_truth_table
  implicit none
  integer :: checks
  checks=17
  if (.not. .true.) then
    write(*,'(a)') 'LIO:not_truth_table:not-true-is-false'
    error stop
  else
    checks=checks+1
  end if
  if (.not. .false.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:not_truth_table:not-false-is-true'
    error stop
  end if
  if (checks /= 19) then
    write(*,'(a)') 'LIO:not_truth_table:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION NOT TRUTH TABLE OK'
end program lio_not_truth_table

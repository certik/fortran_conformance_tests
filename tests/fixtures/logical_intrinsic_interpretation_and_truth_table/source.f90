program lio_and_truth_table
  implicit none
  integer :: checks
  checks=17
  if (.true. .and. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:and_truth_table:and-tt'
    error stop
  end if
  if (.true. .and. .false.) then
    write(*,'(a)') 'LIO:and_truth_table:and-tf'
    error stop
  else
    checks=checks+1
  end if
  if (.false. .and. .true.) then
    write(*,'(a)') 'LIO:and_truth_table:and-ft'
    error stop
  else
    checks=checks+1
  end if
  if (.false. .and. .false.) then
    write(*,'(a)') 'LIO:and_truth_table:and-ff'
    error stop
  else
    checks=checks+1
  end if
  if (checks /= 21) then
    write(*,'(a)') 'LIO:and_truth_table:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION AND TRUTH TABLE OK'
end program lio_and_truth_table

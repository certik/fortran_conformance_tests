program lio_or_truth_table
  implicit none
  integer :: checks
  checks=17
  if (.true. .or. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:or_truth_table:or-tt'
    error stop
  end if
  if (.true. .or. .false.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:or_truth_table:or-tf'
    error stop
  end if
  if (.false. .or. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:or_truth_table:or-ft'
    error stop
  end if
  if (.false. .or. .false.) then
    write(*,'(a)') 'LIO:or_truth_table:or-ff'
    error stop
  else
    checks=checks+1
  end if
  if (checks /= 21) then
    write(*,'(a)') 'LIO:or_truth_table:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION OR TRUTH TABLE OK'
end program lio_or_truth_table

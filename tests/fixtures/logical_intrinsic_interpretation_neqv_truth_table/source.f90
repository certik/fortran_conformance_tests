program lio_neqv_truth_table
  implicit none
  integer :: checks
  checks=17
  if (.true. .neqv. .true.) then
    write(*,'(a)') 'LIO:neqv_truth_table:neqv-tt'
    error stop
  else
    checks=checks+1
  end if
  if (.true. .neqv. .false.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:neqv_truth_table:neqv-tf'
    error stop
  end if
  if (.false. .neqv. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:neqv_truth_table:neqv-ft'
    error stop
  end if
  if (.false. .neqv. .false.) then
    write(*,'(a)') 'LIO:neqv_truth_table:neqv-ff'
    error stop
  else
    checks=checks+1
  end if
  if (checks /= 21) then
    write(*,'(a)') 'LIO:neqv_truth_table:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION NEQV TRUTH TABLE OK'
end program lio_neqv_truth_table

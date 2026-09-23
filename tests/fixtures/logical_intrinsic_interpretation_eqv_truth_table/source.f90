program lio_eqv_truth_table
  implicit none
  integer :: checks
  checks=17
  if (.true. .eqv. .true.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:eqv_truth_table:eqv-tt'
    error stop
  end if
  if (.true. .eqv. .false.) then
    write(*,'(a)') 'LIO:eqv_truth_table:eqv-tf'
    error stop
  else
    checks=checks+1
  end if
  if (.false. .eqv. .true.) then
    write(*,'(a)') 'LIO:eqv_truth_table:eqv-ft'
    error stop
  else
    checks=checks+1
  end if
  if (.false. .eqv. .false.) then
    checks=checks+1
  else
    write(*,'(a)') 'LIO:eqv_truth_table:eqv-ff'
    error stop
  end if
  if (checks /= 21) then
    write(*,'(a)') 'LIO:eqv_truth_table:check-total'
    error stop
  end if
  write(*,'(a)') 'LOGICAL INTRINSIC INTERPRETATION EQV TRUTH TABLE OK'
end program lio_eqv_truth_table

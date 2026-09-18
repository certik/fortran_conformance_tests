program data_position_array_effect
  implicit none
  integer :: a(2,3), checks
  data a /11,21,12,22,13,23/
  checks=0
  if (a(1,1) /= 11) then
    write(*,'(a)') 'DPE:array:a11'
    error stop
  end if
  checks=checks+1
  if (a(2,1) /= 21) then
    write(*,'(a)') 'DPE:array:a21'
    error stop
  end if
  checks=checks+1
  if (a(1,2) /= 12) then
    write(*,'(a)') 'DPE:array:a12'
    error stop
  end if
  checks=checks+1
  if (a(2,2) /= 22) then
    write(*,'(a)') 'DPE:array:a22'
    error stop
  end if
  checks=checks+1
  if (a(1,3) /= 13) then
    write(*,'(a)') 'DPE:array:a13'
    error stop
  end if
  checks=checks+1
  if (a(2,3) /= 23) then
    write(*,'(a)') 'DPE:array:a23'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'DPE:array:check-total'
    error stop
  end if
  write(*,'(a)') 'DATA POSITION ARRAY OK'
end program data_position_array_effect

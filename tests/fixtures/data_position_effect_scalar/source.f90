program data_position_scalar_effect
  implicit none
  integer :: i, j, k, checks
  data i,j,k /11,22,33/
  checks=0
  if (i /= 11) then
    write(*,'(a)') 'DPE:scalar:i'
    error stop
  end if
  checks=checks+1
  if (j /= 22) then
    write(*,'(a)') 'DPE:scalar:j'
    error stop
  end if
  checks=checks+1
  if (k /= 33) then
    write(*,'(a)') 'DPE:scalar:k'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'DPE:scalar:check-total'
    error stop
  end if
  write(*,'(a)') 'DATA POSITION SCALAR OK'
end program data_position_scalar_effect

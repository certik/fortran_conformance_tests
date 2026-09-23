program allocate_statement_r931_errmsg
  implicit none
  integer, allocatable :: x
  integer :: s, t, source_value
  character(len=9) :: msg
  integer :: checks
  checks=0
  s=-5
  t=-9
  source_value=37
  msg='UNCHANGED'
  allocate(x, source=source_value, stat=s, errmsg=msg)
  if (s /= 0) then
    write(*,'(a)') 'ASTMT:r931_errmsg:stat-zero'
    error stop
  end if
  checks=checks+1
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:r931_errmsg:allocated'
    error stop
  end if
  checks=checks+1
  if (x /= 37) then
    write(*,'(a)') 'ASTMT:r931_errmsg:source-value'
    error stop
  end if
  checks=checks+1
  if (len(msg) /= 9) then
    write(*,'(a)') 'ASTMT:r931_errmsg:errmsg-length'
    error stop
  end if
  checks=checks+1
  if (msg /= 'UNCHANGED') then
    write(*,'(a)') 'ASTMT:r931_errmsg:errmsg-unchanged'
    error stop
  end if
  checks=checks+1
  if (t /= -9) then
    write(*,'(a)') 'ASTMT:r931_errmsg:alternate-stat-untouched'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'ASTMT:r931_errmsg:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT R931 ERRMSG OK'
end program allocate_statement_r931_errmsg

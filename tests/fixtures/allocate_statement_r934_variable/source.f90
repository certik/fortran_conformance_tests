program allocate_statement_r934_variable
  implicit none
  integer, allocatable :: x
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:r934_variable:scalar-allocated'
    error stop
  end if
  checks=checks+1
  x=41
  if (x /= 41) then
    write(*,'(a)') 'ASTMT:r934_variable:scalar-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'ASTMT:r934_variable:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT R934 VARIABLE OK'
end program allocate_statement_r934_variable

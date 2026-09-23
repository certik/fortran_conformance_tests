program allocate_statement_r929_forms
  implicit none
  integer, allocatable :: x
  character(len=:), allocatable :: c
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:r929_forms:bare-allocated'
    error stop
  end if
  checks=checks+1
  x=19
  if (x /= 19) then
    write(*,'(a)') 'ASTMT:r929_forms:bare-payload'
    error stop
  end if
  checks=checks+1
  allocate(character(len=5) :: c)
  if (.not. allocated(c)) then
    write(*,'(a)') 'ASTMT:r929_forms:typed-allocated'
    error stop
  end if
  checks=checks+1
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:r929_forms:typed-length'
    error stop
  end if
  checks=checks+1
  c='abcde'
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:r929_forms:typed-payload-length'
    error stop
  end if
  checks=checks+1
  if (c /= 'abcde') then
    write(*,'(a)') 'ASTMT:r929_forms:typed-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'ASTMT:r929_forms:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT R929 FORMS OK'
end program allocate_statement_r929_forms

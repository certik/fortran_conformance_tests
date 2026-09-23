program allocate_statement_c936_targets
  implicit none
  integer, allocatable :: x
  integer, pointer :: ptr
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:c936_targets:allocatable-object'
    error stop
  end if
  checks=checks+1
  x=43
  if (x /= 43) then
    write(*,'(a)') 'ASTMT:c936_targets:allocatable-object-payload'
    error stop
  end if
  checks=checks+1
  allocate(ptr)
  if (.not. associated(ptr)) then
    write(*,'(a)') 'ASTMT:c936_targets:data-pointer-object'
    error stop
  end if
  checks=checks+1
  ptr=47
  if (ptr /= 47) then
    write(*,'(a)') 'ASTMT:c936_targets:data-pointer-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'ASTMT:c936_targets:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT C936 TARGETS OK'
end program allocate_statement_c936_targets

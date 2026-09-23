program allocate_statement_c937_deferred
  implicit none
  character(len=:), allocatable :: c
  integer :: checks
  checks=0
  allocate(character(len=5) :: c)
  if (.not. allocated(c)) then
    write(*,'(a)') 'ASTMT:c937_deferred:allocated'
    error stop
  end if
  checks=checks+1
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:c937_deferred:length'
    error stop
  end if
  checks=checks+1
  c='vwxyz'
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:c937_deferred:payload-length'
    error stop
  end if
  checks=checks+1
  if (c /= 'vwxyz') then
    write(*,'(a)') 'ASTMT:c937_deferred:payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'ASTMT:c937_deferred:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT C937 DEFERRED OK'
end program allocate_statement_c937_deferred

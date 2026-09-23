program allocate_statement_c949_type_no_source
  implicit none
  character(len=:), allocatable :: c
  integer :: checks
  checks=0
  allocate(character(len=5) :: c)
  if (.not. allocated(c)) then
    write(*,'(a)') 'ASTMT:c949_type_no_source:allocated'
    error stop
  end if
  checks=checks+1
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:c949_type_no_source:length'
    error stop
  end if
  checks=checks+1
  c='vwxyz'
  if (len(c) /= 5) then
    write(*,'(a)') 'ASTMT:c949_type_no_source:payload-length'
    error stop
  end if
  checks=checks+1
  if (c /= 'vwxyz') then
    write(*,'(a)') 'ASTMT:c949_type_no_source:payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'ASTMT:c949_type_no_source:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT C949 TYPE NO SOURCE OK'
end program allocate_statement_c949_type_no_source

program common_list_named_multiple_effect
  implicit none
  integer :: seed_entries, seed_writes, seed_returns
  integer :: writer_entries, writer_writes, writer_returns
  integer :: reader_entries, reader_checks, reader_returns, caller_checks
  external :: seed_common, write_common, read_common
  seed_entries=0
  seed_writes=0
  seed_returns=0
  writer_entries=0
  writer_writes=0
  writer_returns=0
  reader_entries=0
  reader_checks=0
  reader_returns=0
  caller_checks=0
  call seed_common(seed_entries, seed_writes)
  seed_returns=seed_returns+1
  if (seed_entries /= 1) then
    write(*,'(a)') 'CLE:named_multiple:seed-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (seed_writes /= 4) then
    write(*,'(a)') 'CLE:named_multiple:seed-writes'
    error stop
  end if
  caller_checks=caller_checks+1
  if (seed_returns /= 1) then
    write(*,'(a)') 'CLE:named_multiple:seed-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  call write_common(writer_entries, writer_writes)
  writer_returns=writer_returns+1
  if (writer_entries /= 1) then
    write(*,'(a)') 'CLE:named_multiple:writer-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (writer_writes /= 4) then
    write(*,'(a)') 'CLE:named_multiple:writer-writes'
    error stop
  end if
  caller_checks=caller_checks+1
  if (writer_returns /= 1) then
    write(*,'(a)') 'CLE:named_multiple:writer-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  call read_common(reader_entries, reader_checks)
  reader_returns=reader_returns+1
  if (reader_entries /= 1) then
    write(*,'(a)') 'CLE:named_multiple:reader-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (reader_checks /= 4) then
    write(*,'(a)') 'CLE:named_multiple:reader-checks'
    error stop
  end if
  caller_checks=caller_checks+1
  if (reader_returns /= 1) then
    write(*,'(a)') 'CLE:named_multiple:reader-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  if (caller_checks /= 9) then
    write(*,'(a)') 'CLE:named_multiple:caller-check-total'
    error stop
  end if
  write(*,'(a)') 'COMMON LIST NAMED_MULTIPLE OK'
end program common_list_named_multiple_effect

subroutine seed_common(entries, writes)
  implicit none
  integer, intent(inout) :: entries, writes
  integer :: seed_values(4)
  common /packet/ seed_values
  save /packet/
  entries=entries+1
  seed_values(1)=-101
  writes=writes+1
  seed_values(2)=-102
  writes=writes+1
  seed_values(3)=-103
  writes=writes+1
  seed_values(4)=-104
  writes=writes+1
  return
end subroutine seed_common

subroutine write_common(entries, writes)
  implicit none
  integer, intent(inout) :: entries, writes
  integer :: a, b, c, d
  common /packet/ a, b
  common /packet/ c, d
  save /packet/
  entries=entries+1
  a=11
  writes=writes+1
  b=22
  writes=writes+1
  c=33
  writes=writes+1
  d=44
  writes=writes+1
  return
end subroutine write_common

subroutine read_common(entries, checks)
  implicit none
  integer, intent(inout) :: entries, checks
  integer :: view(4)
  common /packet/ view
  save /packet/
  entries=entries+1
  if (view(1) /= 11) then
    write(*,'(a)') 'CLE:named_multiple:position-1'
    error stop
  end if
  checks=checks+1
  if (view(2) /= 22) then
    write(*,'(a)') 'CLE:named_multiple:position-2'
    error stop
  end if
  checks=checks+1
  if (view(3) /= 33) then
    write(*,'(a)') 'CLE:named_multiple:position-3'
    error stop
  end if
  checks=checks+1
  if (view(4) /= 44) then
    write(*,'(a)') 'CLE:named_multiple:position-4'
    error stop
  end if
  checks=checks+1
  return
end subroutine read_common

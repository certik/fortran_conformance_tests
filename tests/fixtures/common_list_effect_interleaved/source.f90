program common_list_interleaved_effect
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
    write(*,'(a)') 'CLE:interleaved:seed-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (seed_writes /= 4) then
    write(*,'(a)') 'CLE:interleaved:seed-writes'
    error stop
  end if
  caller_checks=caller_checks+1
  if (seed_returns /= 1) then
    write(*,'(a)') 'CLE:interleaved:seed-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  call write_common(writer_entries, writer_writes)
  writer_returns=writer_returns+1
  if (writer_entries /= 1) then
    write(*,'(a)') 'CLE:interleaved:writer-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (writer_writes /= 4) then
    write(*,'(a)') 'CLE:interleaved:writer-writes'
    error stop
  end if
  caller_checks=caller_checks+1
  if (writer_returns /= 1) then
    write(*,'(a)') 'CLE:interleaved:writer-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  call read_common(reader_entries, reader_checks)
  reader_returns=reader_returns+1
  if (reader_entries /= 1) then
    write(*,'(a)') 'CLE:interleaved:reader-entries'
    error stop
  end if
  caller_checks=caller_checks+1
  if (reader_checks /= 4) then
    write(*,'(a)') 'CLE:interleaved:reader-checks'
    error stop
  end if
  caller_checks=caller_checks+1
  if (reader_returns /= 1) then
    write(*,'(a)') 'CLE:interleaved:reader-returns'
    error stop
  end if
  caller_checks=caller_checks+1
  if (caller_checks /= 9) then
    write(*,'(a)') 'CLE:interleaved:caller-check-total'
    error stop
  end if
  write(*,'(a)') 'COMMON LIST INTERLEAVED OK'
end program common_list_interleaved_effect

subroutine seed_common(entries, writes)
  implicit none
  integer, intent(inout) :: entries, writes
  integer :: seed_left(2), seed_right(2)
  common /left_block/ seed_left
  common /right_block/ seed_right
  save /left_block/
  save /right_block/
  entries=entries+1
  seed_left(1)=-101
  writes=writes+1
  seed_left(2)=-102
  writes=writes+1
  seed_right(1)=-103
  writes=writes+1
  seed_right(2)=-104
  writes=writes+1
  return
end subroutine seed_common

subroutine write_common(entries, writes)
  implicit none
  integer, intent(inout) :: entries, writes
  integer :: a, b, x, y
  common /left_block/ a
  common /right_block/ x
  common /left_block/ b
  common /right_block/ y
  save /left_block/
  save /right_block/
  entries=entries+1
  a=11
  writes=writes+1
  x=33
  writes=writes+1
  b=22
  writes=writes+1
  y=44
  writes=writes+1
  return
end subroutine write_common

subroutine read_common(entries, checks)
  implicit none
  integer, intent(inout) :: entries, checks
  integer :: left_view(2), right_view(2)
  common /left_block/ left_view
  common /right_block/ right_view
  save /left_block/
  save /right_block/
  entries=entries+1
  if (left_view(1) /= 11) then
    write(*,'(a)') 'CLE:interleaved:left-1'
    error stop
  end if
  checks=checks+1
  if (left_view(2) /= 22) then
    write(*,'(a)') 'CLE:interleaved:left-2'
    error stop
  end if
  checks=checks+1
  if (right_view(1) /= 33) then
    write(*,'(a)') 'CLE:interleaved:right-1'
    error stop
  end if
  checks=checks+1
  if (right_view(2) /= 44) then
    write(*,'(a)') 'CLE:interleaved:right-2'
    error stop
  end if
  checks=checks+1
  return
end subroutine read_common

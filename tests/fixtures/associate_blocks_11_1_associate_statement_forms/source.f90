! rule: R1103
! covers: unnamed-associate-stmt, named-associate-stmt, multiple-association-list
program ab_r1103_stmt
  implicit none
  integer :: x, y, named_seen, unnamed_seen, multi_seen
  x=2; y=5; named_seen=-1; unnamed_seen=-2; multi_seen=-3
  associate (u => x)
    unnamed_seen=u+10
  end associate
  named: associate (n => y)
    named_seen=n+20
  end associate named
  associate (a => x, b => y)
    multi_seen=a*10+b
  end associate
  if (unnamed_seen /= 12) then
    write(*,'(a)') 'UNNAMED'
    error stop
  end if
  if (named_seen /= 25) then
    write(*,'(a)') 'NAMED'
    error stop
  end if
  if (multi_seen /= 25) then
    write(*,'(a)') 'MULTI'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS R1103 STMT OK'

end program ab_r1103_stmt

! rule: R1106
! covers: unnamed-end-associate, named-end-associate
program ab_r1106_end
  implicit none
  integer :: x, y
  x=1; y=2
  associate (a => x)
    a=11
  end associate
  named_end: associate (b => y)
    b=22
  end associate named_end
  if (x /= 11) then
    write(*,'(a)') 'R1106U'
    error stop
  end if
  if (y /= 22) then
    write(*,'(a)') 'R1106N'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS R1106 END OK'

end program ab_r1106_end

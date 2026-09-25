! rule: S11.1.3.3-004
! covers: contiguity-iff-selector
program ab1133_contiguity
  implicit none
  integer :: base(6), contiguous_seen, strided_seen
  base=[1,2,3,4,5,6]; contiguous_seen=-1; strided_seen=-1
  associate (whole => base)
    if (is_contiguous(whole)) contiguous_seen=1
  end associate
  associate (stride => base(1:6:2))
    if (.not. is_contiguous(stride)) strided_seen=1
  end associate
  if (contiguous_seen /= 1) then
    write(*,'(a)') 'CONTIG'
    error stop
  end if
  if (strided_seen /= 1) then
    write(*,'(a)') 'STRIDE'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS CONTIGUITY OK'

end program ab1133_contiguity

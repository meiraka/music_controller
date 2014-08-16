import setpath
setpath.update()

from music_controller import listfilter
from music_controller.core import client


class TestModel:
    """Test for music_controller.listfilter"""
    TEST_SETTINGS = [
        [(u'album', listfilter.CRITERIA_STYLE_ROOT),
            (u'%album%', listfilter.CRITERIA_STYLE_ALBUM),
            (u'%disc% %track_index% %title%', listfilter.CRITERIA_STYLE_SONG)],
        [(u'genre', listfilter.CRITERIA_STYLE_ROOT),
            (u'%genre%', listfilter.CRITERIA_STYLE_DEFAULT),
            (u'%album%', listfilter.CRITERIA_STYLE_ALBUM),
            (u'%disc% %track_index% %title%', listfilter.CRITERIA_STYLE_SONG)]]

    TEST_SORTER = '%albumartist% %disc% %date% %album% %track_index% %title%'

    SONGS = [
        client.Song(dict(album=u'album1', title=u'title11', genre=u'genre1')),
        client.Song(dict(album=u'album1', title=u'title12', genre=u'genre1')),
        client.Song(dict(album=u'album2', title=u'title21', genre=u'genre1')),
        client.Song(dict(album=u'album3', title=u'title31', genre=u'genre2'))]

    def test_show_root_child(self):
        """Returns toplevel closed child model from root model."""
        print setpath.sys.path
        model = listfilter.Model(self.SONGS,
                                 self.TEST_SETTINGS, self.TEST_SORTER)
        assert self.SONGS == model.songs
        assert 2 == len(model.childlen)
        assert u'album' == model.childlen[0][0]
        assert False == model.childlen[0][1].is_open()
        assert self.SONGS == model.childlen[0][1].songs
        assert u'genre' == model.childlen[1][0]
        assert False == model.childlen[1][1].is_open()
        assert self.SONGS == model.childlen[1][1].songs

    def test_child_open(self):
        """album child model grouping by album."""
        print setpath.sys.path
        model = listfilter.Model(self.SONGS,
                                 self.TEST_SETTINGS, self.TEST_SORTER)
        assert self.SONGS == model.songs
        child_model = model.childlen[0][1]
        child_model.open()
        assert 3 == len(child_model.childlen)

        # key: label, value: list of songs
        label_songs = {}
        for label, song in [(song.format('%album%'), song)
                            for song in self.SONGS]:
            label_songs.setdefault(label, [])
            label_songs[label].append(song)

        for label, sub_child in child_model.childlen:
            assert label_songs[label] == sub_child.songs
